# Qué es IceFlix
IceFlix es una aplicación escrita en Python que simula un conjunto de microservicios capaces de 
almacenar y reproducir video por demanda en streaming.

Está compuesto por un servicio principal al que se conecta el usuario, y capaz de comunicarse 
con los siguientes servicios:
- Servicio de autenticación (maneja usuarios y contraseñas)
- Servicio de catálogo (encargado de listar los medios disponibles)
- Servicio de streaming (encargado de enviar el video por streaming al cliente)

La aplicación dispone de un modo de administrador que permite manejar la base de datos de usuarios
y los medios.
<br/><br/>

## Requisitos
Para ejecutar la aplicación y poder reproducir los medios hacen falta las siguientes dependencias:

```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv B6391CB2CFBA643D  
sudo apt-add-repository "deb http://zeroc.com/download/ice/3.7/ubuntu20.04 stable main"  
sudo apt-get update  
sudo apt-get install libzeroc-icestorm3.7 zeroc-icebox  
sudo apt-get install zeroc-ice-utils  
sudo apt-get install vlc  
pip install python-vlc
```

## Integrantes del equipo:  
- Sergio Garrido Merino (https://github.com/sergiogm8)
- Álvaro Fernández Santos (https://github.com/AlvaroFernandezSantos) 
- Daniel Almansa Rodríguez (https://github.com/DanielAlmansaRodriguez)

## Información útil:  
- **Token de administración**: admin  
- **Username**: user  
- **Contraseña**: password  
- **Proxy servicio IceFlix::Main** -> MainPrincipal -t -e 1.1 @ MainAdapter1
- **Proxy servicio IceFlix::StreamProvider** -> ProviderPrincipal -t -e 1.1 @ StreamProviderAdapter1
- **Medios de ejemplo**: Pelucas.mp4  
- **La carpeta resources simula ser el servidor de archivos.**  
- **La carpeta local simula ser el equipo del administrador, por lo que los archivos que se quieran subir al servidor deben estar en esta carpeta.**

## Cómo reproducir un medio:
1. Ejecutar "run_iceflix"
2. Ejecutar "run_client"
3. Introducir el proxy al servicio IceFlix::Main()
4. Seleccionar <2> e introducir "user" como usuario y "password" como contraseña
5. Seleccionar <4>, seleccionar <1>, seleccionar <1>
6. Insertar título (Pelucas)
7. Seleccionar <1>
8. Seleccionar <1> para reproducir