# PoC de ReleaseWeave

ReleaseWeave es el nuevo nombre de ChangeForge, incluido su repositorio público. Es un CLI de Rust inspirado en Changesets para documentar cambios, calcular versiones y preparar releases de GitHub. El mismo flujo funciona en un single-repo y en un monorepo con versiones independientes.

## Ejecutar y ver resultados reales

Desde la raíz de este checkout:

```sh
cargo build --release --locked
python3 scripts/demo.py
```

El script imprime cada comando y su salida real. Crea copias nuevas de `examples/single-repo` y `examples/monorepo` dentro de `.demo/FECHA/`. Los originales quedan disponibles para repetir la prueba. Al terminar deja:

- `report.json`: versiones, tags y notas de los dos escenarios.
- `transcript.json`: comandos ejecutados y sus salidas.
- `single-repo/`: manifiesto Rust actualizado, CHANGELOG y metadata de release.
- `monorepo/`: dos paquetes actualizados y un worker sin cambios.
- Workflows de GitHub generados en cada ejemplo.

El runner comprueba que dry-run no modifica ningún archivo y que después del bump no quedan changesets pendientes. No crea tags, PRs ni releases remotos.

## Qué muestra el single-repo

```sh
./target/release/releaseweave --root RUTA_A_UNA_COPIA init --yes
./target/release/releaseweave --root RUTA_A_UNA_COPIA create --bump minor --message "Add a configurable greeting"
./target/release/releaseweave --root RUTA_A_UNA_COPIA plan
./target/release/releaseweave --root RUTA_A_UNA_COPIA bump --dry-run
./target/release/releaseweave --root RUTA_A_UNA_COPIA bump
```

`hello-release` pasa de 1.2.3 a 1.3.0. Se crea un CHANGELOG, se consume el changeset y se registra el tag propuesto `v1.3.0`. El comando bump no publica ese tag.

## Qué muestra el monorepo

| Paquete | Cambio solicitado | Versión final | GitHub tag propuesto |
| --- | --- | --- | --- |
| acme-api | minor | 1.5.0 | acme-api/v1.5.0 |
| @acme/web | patch | 2.1.1 | @acme/web/v2.1.1 |
| acme-worker | ninguno | 0.7.2 | ninguno |

Cada paquete afectado obtiene su propio CHANGELOG. El worker conserva su manifiesto y no obtiene un release. La demostración usa un workspace de Cargo con versiones explícitas y un manifiesto npm para mostrar el uso en un monorepo mixto.

Puedes seleccionar varios paquetes repitiendo `--package`; con flags todos reciben el mismo nivel de bump. Para niveles distintos se pueden crear changesets separados o editar la tabla `[releases]` de un changeset.

## Flujo real en GitHub

Cambio de código + changeset → push a main → PR de versiones → revisión y merge → GitHub Releases por paquete.

`init --github` genera los workflows. El release se ejecuta solo para una PR fusionada desde `releaseweave/releases`, del mismo repositorio, y se fija al SHA del merge. El contenido de `.releaseweave/release.json` contiene las versiones, tags y notas calculados por el CLI.

El repositorio público es https://github.com/ricardoleal20/ReleaseWeave y los templates de consumidores apuntan a `ricardoleal20/ReleaseWeave@main`. La CI del PoC y el workflow que prepara PRs de release ya se han ejecutado en GitHub. La publicación real de un release sigue reservada al merge de una PR de versiones; las pruebas de publicación usan repositorios Git locales y una frontera gh simulada.

## Alcance y límites

Hay soporte de manifiestos Cargo.toml, package.json y pyproject.toml; cambios independientes de paquetes; errores con código de salida distinto de cero; dry-run; salida JSON; compatibilidad con el formato anterior para single-repo; actualización de entradas locales de Cargo.lock; y conservación de archivos ajenos a los changesets.

Este PoC no propaga automáticamente bumps ni rangos de dependencias internas, no interpreta Cargo `version.workspace`, no publica a npm/crates.io/PyPI y no implementa prereleases ni grupos de versiones fijas. Los lockfiles distintos de Cargo deben regenerarse con su package manager. Las funciones experimentales de IA y autocommit del CLI anterior quedan fuera del PoC, para que la demostración funcione sin credenciales ni servicios externos.

Si un bump rompe un rango de dependencia local de Cargo, el plan se bloquea antes de escribir y pide actualizar el rango manualmente. Se comprueban también consumidores del workspace que no están seleccionados para release. Las dependencias del registry con el mismo nombre no se confunden con las locales.

Las operaciones preparan todos los archivos antes de reemplazarlos y restauran contenido ante errores de IO normales. No constituyen una transacción atómica frente a un corte de energía o kill; si se interrumpe un proceso, se debe revisar el diff antes de retirar su lock.
