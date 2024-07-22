# TAER-Core module

This module represents the Core of TAER App. This module is not intended to be accessible to app users and it should be modified by app developers only. It is based on the [wxPython](https://wiki.wxpython.org) framework and the architecture is the well-known [Model-View-Controller](https://wiki.wxpython.org/ModelViewController) pattern. The components are organized as follows:

- Model: &nbsp; &nbsp; &nbsp; &nbsp; [main_model.py](src\TAER_Core\main_model.py)
- Controller: &nbsp; [main_presenter.py](src\TAER_Core\main_presenter.py) | [delegates.py](src\TAER_Core\Controllers\delegates.py) | [interactors.py](src\TAER_Core\Controllers\interactors.py)
- View: &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; [main_view.py](src\TAER_Core\main_view.py) | [Views](src\TAER_Core\Views)