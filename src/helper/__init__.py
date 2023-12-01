from .helpers_cadquery import HelperCadquery
from .helpers_solid import HelperSolid

def Helper(engine):
        if engine == 'cadquery':
            return HelperCadquery()
        elif engine == 'solid':
            return HelperSolid()
        else:
            raise ValueError("engine must be one of; cadquery, solid")
