from fivcadvisor.models import providers
from importlib import import_module


# print(providers.__name__)

m = import_module(f'{providers.__name__}.langchain')
print(m.get_model())
