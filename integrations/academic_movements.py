from typing import Protocol
class AcademicMovementsAdapter(Protocol):
    """Future authorized integration; must return evidence-backed exception rows."""
    def fetch(self,matricula:str)->list[dict]:...
