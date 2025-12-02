# PickVs

## TODO
- [ ] drop and recreate tables
- [ ] reupload historical data

## Development
pixi is used for Python package management for the backend, install that first if necessary. Then go into the directory, and install dependencies. 

```bash
cd backend
pixi install
```
Then to run a dev server:

```bash
pixi run dev
```
Run tests with:
```bash
pixi run test
```
Type check/lint using Pyrefly and Ruff:
```bash
pixi run lint
```
Format using Ruff:
```bash
pixi run format
```
