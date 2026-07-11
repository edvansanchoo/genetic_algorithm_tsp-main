"""Ponto de entrada da interface Web."""

import uvicorn

from traveling_salesman_problem.web.server import create_app
from traveling_salesman_problem.web.simulation_service import SimulationService


def main() -> None:
    service = SimulationService()
    service.startup()
    app = create_app(service)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
