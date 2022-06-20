# Servicio IceFlix del grupo ADS
https://github.com/SSDD-2021-2022/SSDD_Lab_Team_ADS

## Integrantes del equipo:  
- Sergio Garrido Merino (Sergio.Garrido5@alu.uclm.es)
- Álvaro Fernández Santos (Alvaro.Fernanz@alu.uclm.es) 
- Daniel Almansa Rodríguez (Daniel.Almansa1@alu.uclm.es)

## Información útil:  
- **Token de administración**: admin  
- **Username**: user  
- **Contraseña**: password  
- **Proxy servicio IceFlix::Main** -> MainPrincipal -t -e 1.1 @ MainAdapter1
- **Proxy servicio IceFlix::StreamProvider** -> StreamProvider:tcp -p 9095
- **Medios de ejemplo**: Pelucas.mp4  
- **La carpeta resources simula ser el servidor de archivos.**  
- **La carpeta local simula ser el equipo del administrador, por lo que los archivos que se quieran subir al servidor deben estar en esta carpeta.**

## Cómo reproducir un medio:
1. Ejecutar "run_iceflix"
2. Ejecutar "run_client"
3. Introducir el proxy al servicio IceFlix::Main()
4. Seleccionar <2> e introducir usuario y contraseña
5. Seleccionar <4>, seleccionar <1>, seleccionar <1>
6. Insertar título (Pelucas)
7. Seleccionar <1>
8. Seleccionar <1> para reproducir

## Cómo cambiar el nombre de un medio:
1. Ejecutar "run_iceflix"
2. Ejecutar "run_client"
3. Introducir el proxy al servicio IceFlix::Main()
4. Seleccionar <1> e introducir el token de administración (admin)
5. Seleccionar <4>, seleccionar <1>, seleccionar <1>
6. Insertar título (Pelucas)
7. Seleccionar <1>
8. Seleccionar <4> para renombrar

## Cómo añadir tags a un medio:
1. Ejecutar "run_iceflix"
2. Ejecutar "run_client"
3. Introducir el proxy al servicio IceFlix::Main()
4. Seleccionar <2> e introducir usuario y contraseña
5. Seleccionar <4>, seleccionar <1>, seleccionar <1>
6. Insertar título (Pelucas)
7. Seleccionar <1>
8. Seleccionar <2> para añadir tags
9. Introduce <nombre de tag> y deja vacío para confirmar
