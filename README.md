# Template project for ssdd-lab

This repository is a Python project template. It contains the
following files and directories:

- `packagename` is the main Python package. You should rename it to
  something meaninful for your project.
- `packagename/__init__.py` is an empty file needed by Python to
  recognise the `packagename` directory as a Python package/module.
- `packagename/cli.py` contains several functions that can handle the
  basic console entry points defined in `python.cfg`. The name of the
  submodule and the functions can be modified if you need.
- `pyproject.toml` defines the build system used in the project.
- `run_client` should be a script that can be run directly from the
  repository root directory. It should be able to run the IceFlix
  client.
- `run_iceflix` should be a script that can be run directly from the
  repository root directory. It should be able to run all the services
  in background in order to test the whole system.
- `setup.cfg` is a Python distribution configuration file for
  Setuptools. It needs to be modified in order to adeccuate to the
  package name and console handler functions.

Información para probar la práctica:
Token de administración: admin
Username: user
Contraseña: password
Medios de ejemplo: Esponja.mp4, Peluquero.mp4

Cómo reproducir un medio:
1. Ejecutar "run_iceflix"
2. Ejecutar "run_client"
3. Introducir el proxy al servicio IceFlix::Main()
4. Seleccionar <numero> e introducir usuario y contraseña
5. Seleccionar <numero> e introducir <Nombre de medio>
6. Introducir <n>
7. Seleccionar <1> para reproducir


Cómo editar el nombre de un medio:
1. Ejecutar "run_iceflix"
2. Ejecutar "run_client"
3. Introducir el proxy al servicio IceFlix::Main()
4. Seleccionar <numero> e introducir el token de administración
5. Seleccionar <numero> e introducir <Nombre de medio>