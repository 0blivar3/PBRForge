from __future__ import annotations
from pathlib import Path
import numpy as np
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QPixmap, QImage
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog, QMessageBox, QSplitter, QScrollArea,
    QComboBox, QSlider, QStatusBar, QProgressBar, QInputDialog)
from core.image_io import load_image
from core.project import save_project, load_project
from exporter.exporter import export_maps
from workers.generation_worker import GenerationWorker

class ImagePreview(QScrollArea):
    def __init__(self):
        super().__init__()
        self.label = QLabel("Import a texture to begin")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setMinimumSize(320, 240)
        self.label.setStyleSheet("color: #8993a2;")
        self.setWidget(self.label)
        self.setWidgetResizable(True)
        self._pixmap = None
    def set_array(self, array: np.ndarray):
        arr = np.ascontiguousarray(array)
        if arr.ndim == 2:
            arr = np.repeat(arr[..., None], 3, axis=2)
        if arr.shape[2] == 4:
            fmt = QImage.Format.Format_RGBA8888
        else:
            arr, fmt = arr[..., :3], QImage.Format.Format_RGB888
        h, w, c = arr.shape
        self._pixmap = QPixmap.fromImage(QImage(arr.data, w, h, c*w, fmt).copy())
        self._refresh()
    def _refresh(self):
        if self._pixmap:
            self.label.setPixmap(self._pixmap.scaled(self.viewport().size(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PBRForge — Material Creation Studio")
        self.resize(1420, 900)
        self.source = None
        self.source_path = None
        self.maps: dict[str, np.ndarray] = {}
        self.current_map = "source"
        self._thread = self._worker = None
        self._build_ui()
        self._build_menu()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — import a texture to create a material")

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.map_list = QListWidget()
        self.map_list.addItems(["Source / Albedo", "Height", "Normal", "Roughness"])
        self.map_list.currentRowChanged.connect(self._select_map)
        self.map_list.setMinimumWidth(170)
        splitter.addWidget(self.map_list)
        center = QWidget()
        center_layout = QVBoxLayout(center)
        toolbar = QHBoxLayout()
        self.preview_title = QLabel("2D Texture Preview")
        self.preview_title.setStyleSheet("font-size: 14pt; font-weight: 600;")
        toolbar.addWidget(self.preview_title)
        toolbar.addStretch()
        fit = QPushButton("Fit to window")
        fit.clicked.connect(self._refresh_preview)
        toolbar.addWidget(fit)
        center_layout.addLayout(toolbar)
        self.preview = ImagePreview()
        center_layout.addWidget(self.preview, 1)
        self.info_label = QLabel("No texture loaded")
        self.info_label.setObjectName("muted")
        center_layout.addWidget(self.info_label)
        splitter.addWidget(center)
        panel = QWidget()
        panel.setMinimumWidth(260)
        controls = QVBoxLayout(panel)
        controls.addWidget(QLabel("Generation settings"))
        self.method = QComboBox()
        self.method.addItems(["luminance", "grayscale", "edges", "combined"])
        controls.addWidget(QLabel("Height method"))
        controls.addWidget(self.method)
        self.strength = self._slider(1, 100, 40)
        controls.addWidget(QLabel("Normal strength"))
        controls.addWidget(self.strength)
        self.contrast = self._slider(10, 300, 100)
        controls.addWidget(QLabel("Contrast"))
        controls.addWidget(self.contrast)
        self.blur = self._slider(0, 100, 0)
        controls.addWidget(QLabel("Blur radius"))
        controls.addWidget(self.blur)
        self.detail = self._slider(0, 200, 50)
        controls.addWidget(QLabel("Detail"))
        controls.addWidget(self.detail)
        self.convention = QComboBox()
        self.convention.addItems(["OpenGL (Y+)", "DirectX (Y−)"])
        controls.addWidget(QLabel("Normal convention"))
        controls.addWidget(self.convention)
        for label, key in [("Generate Height", "height"), ("Generate Normal", "normal"),
                           ("Generate Roughness", "roughness")]:
            button = QPushButton(label)
            button.setMinimumHeight(38)
            button.clicked.connect(lambda checked=False, k=key: self._generate(k))
            controls.addWidget(button)
        controls.addStretch()
        splitter.addWidget(panel)
        splitter.setSizes([190, 900, 300])
        layout.addWidget(splitter, 1)
        bottom = QHBoxLayout()
        self.operation = QLabel("Idle")
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(180)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        bottom.addWidget(self.operation)
        bottom.addStretch()
        bottom.addWidget(self.progress)
        layout.addLayout(bottom)
        self.setCentralWidget(root)

    def _slider(self, low, high, value):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setValue(value)
        return slider

    def _build_menu(self):
        menu = self.menuBar().addMenu("File")
        for label, callback in [("Import Texture…", self._import_image),
                                ("Open Project…", self._open_project),
                                ("Save Project…", self._save_project),
                                ("Export Material…", self._export)]:
            action = QAction(label, self)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)

    def _import_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import source texture", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.tga *.webp)")
        if not path:
            return
        try:
            self.source = load_image(path)
            self.source_path = Path(path)
            self.maps.clear()
            self.map_list.setCurrentRow(0)
            self._show_array(self.source, "Source / Albedo")
            h, w = self.source.shape[:2]
            self.info_label.setText(f"{w} × {h} px   •   {Path(path).stat().st_size / 1024:.1f} KB")
            self.statusBar().showMessage(f"Loaded {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))

    def _select_map(self, row):
        keys = ["source", "height", "normal", "roughness"]
        if row < 0:
            return
        key = keys[row]
        self.current_map = key
        if key == "source" and self.source is not None:
            self._show_array(self.source, "Source / Albedo")
        elif key in self.maps:
            self._show_array(self.maps[key], key.title())
        else:
            self.preview.label.setPixmap(QPixmap())
            self.preview.label.setText(f"{key.title()} has not been generated yet")

    def _show_array(self, array, title):
        self.preview_title.setText(f"2D Texture Preview — {title}")
        self.preview.set_array(array)

    def _refresh_preview(self):
        if self.current_map == "source" and self.source is not None:
            self._show_array(self.source, "Source / Albedo")
        elif self.current_map in self.maps:
            self._show_array(self.maps[self.current_map], self.current_map.title())

    def _generate(self, map_name):
        if self.source is None:
            QMessageBox.information(self, "No source", "Import a source texture first.")
            return
        if self._thread is not None:
            return
        blur = self.blur.value() / 10.0
        contrast, detail = self.contrast.value() / 100.0, self.detail.value() / 100.0
        params = {}
        if map_name == "height":
            params = {"method": self.method.currentText(), "contrast": contrast,
                      "detail": detail, "blur": blur}
        elif map_name == "normal":
            params = {"strength": self.strength.value() / 10.0, "blur": blur,
                      "convention": "opengl" if self.convention.currentIndex() == 0 else "directx"}
            if "height" in self.maps:
                params["height_map"] = self.maps["height"]
        else:
            params = {"method": "detail", "contrast": contrast, "detail": detail, "blur": blur}
        self._thread = QThread(self)
        self._worker = GenerationWorker(self.source.copy(), map_name, params)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._generation_done)
        self._worker.failed.connect(self._generation_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self.progress.setRange(0, 0)
        self.operation.setText(f"Generating {map_name}…")
        self._thread.start()

    def _generation_done(self, name, result):
        self.maps[name] = result
        self.map_list.setCurrentRow({"height": 1, "normal": 2, "roughness": 3}[name])
        self._show_array(result, name.title())
        self.operation.setText(f"{name.title()} generated")
        self.statusBar().showMessage(f"{name.title()} map generated successfully")

    def _generation_failed(self, message):
        self.operation.setText("Generation failed")
        QMessageBox.critical(self, "Generation failed", message)

    def _cleanup_worker(self):
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self._worker = self._thread = None

    def _save_project(self):
        if self.source is None:
            QMessageBox.information(self, "No project", "Import a texture first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PBRForge project",
            "Material.pbrforge", "PBRForge Project (*.pbrforge)")
        if not path:
            return
        if not path.lower().endswith(".pbrforge"):
            path += ".pbrforge"
        try:
            save_project(path, self.source, self.maps, Path(path).stem)
            self.statusBar().showMessage(f"Project saved: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PBRForge project", "",
            "PBRForge Project (*.pbrforge)")
        if not path:
            return
        try:
            self.source, self.maps, manifest = load_project(path)
            self.source_path = None
            self.map_list.setCurrentRow(0)
            self._show_array(self.source, "Source / Albedo")
            h, w = self.source.shape[:2]
            self.info_label.setText(f"{w} × {h} px   •   {manifest.get('name', 'Material')}")
            self.statusBar().showMessage(f"Opened project: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))

    def _export(self):
        if self.source is None:
            QMessageBox.information(self, "No material", "Import a texture first.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Choose export directory")
        if not directory:
            return
        name, ok = QInputDialog.getText(self, "Material name", "Name:", text="Material")
        if not ok or not name.strip():
            return
        try:
            files = export_maps(directory, name.strip(), self.source, self.maps,
                                normal_convention=self.convention.currentText())
            QMessageBox.information(self, "Export complete",
                                    f"Exported {len(files)} files to:\n{directory}")
        except FileExistsError as exc:
            answer = QMessageBox.question(self, "Files already exist",
                f"{exc}\nOverwrite existing material files?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.Yes:
                try:
                    files = export_maps(directory, name.strip(), self.source, self.maps,
                        normal_convention=self.convention.currentText(), overwrite=True)
                    QMessageBox.information(self, "Export complete", f"Exported {len(files)} files.")
                except Exception as retry_exc:
                    QMessageBox.critical(self, "Export failed", str(retry_exc))
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
