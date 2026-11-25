from __future__ import annotations
from PySide6.QtCore import QObject, Signal, Slot
from generators.height import generate_height
from generators.normal import generate_normal
from generators.roughness import generate_roughness

class GenerationWorker(QObject):
    finished = Signal(str, object)
    failed = Signal(str)
    def __init__(self, source, map_name: str, parameters: dict):
        super().__init__()
        self.source, self.map_name, self.parameters = source, map_name, parameters
    @Slot()
    def run(self):
        try:
            params = dict(self.parameters)
            if self.map_name == "height":
                result = generate_height(self.source, **params)
            elif self.map_name == "normal":
                height = params.pop("height_map", None)
                if height is None:
                    height = generate_height(self.source)
                result = generate_normal(height, **params)
            elif self.map_name == "roughness":
                result = generate_roughness(self.source, **params)
            else:
                raise ValueError(f"Unknown map: {self.map_name}")
            self.finished.emit(self.map_name, result)
        except Exception as exc:
            self.failed.emit(str(exc))
