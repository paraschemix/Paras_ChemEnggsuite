from domains.dom_06_process_safety.psv_engine import REGISTRY as _existing
from domains.dom_06_process_safety.relief_scenarios_engine import REGISTRY as _relief
from domains.dom_06_process_safety.orifice_sizing_engine import REGISTRY as _orifice
from domains.dom_06_process_safety.flare_koDrum_engine import REGISTRY as _flare_ko
from domains.dom_06_process_safety.bund_containment_engine import REGISTRY as _bund

REGISTRY = {**_existing, **_relief, **_orifice, **_flare_ko, **_bund}
