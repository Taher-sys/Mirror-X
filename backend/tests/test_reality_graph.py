"""Software test fixtures and verification tests for Reality Graph parsers and ingestion."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ingestion.engine import IngestionEngine
from app.models.organization import Organization
from app.models.project import Project
from app.models.repository import Repository

# --- Fixtures for 10 supported formats ---

FIXTURE_PACKAGE_JSON = """{
  "name": "checkout-frontend",
  "version": "2.4.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build"
  },
  "dependencies": {
    "react": "^18.3.1",
    "next": "14.2.14",
    "axios": "^1.7.0"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}"""

FIXTURE_PYPROJECT_TOML = """[project]
name = "order-service"
version = "1.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "sqlalchemy>=2.0.35",
    "httpx>=0.27.0"
]
"""

FIXTURE_REQUIREMENTS_TXT = """# Core dependencies
pydantic>=2.10.0
alembic>=1.13.2
aiomysql>=0.2.0
"""

FIXTURE_DOCKERFILE = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8000
ENTRYPOINT ["uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
"""

FIXTURE_DOCKER_COMPOSE = """version: '3.8'
services:
  web:
    image: order-service:latest
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  db:
    image: mysql:8.0
    ports:
      - "3306:3306"
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
"""

FIXTURE_OPENAPI_YAML = """openapi: 3.0.3
info:
  title: Order Processing API
  version: 1.0.0
paths:
  /api/v1/orders:
    get:
      summary: List all orders
      operationId: listOrders
      responses:
        '200':
          description: OK
    post:
      summary: Create new customer order
      operationId: createOrder
      responses:
        '201':
          description: Created
  /api/v1/orders/{order_id}:
    get:
      summary: Get order details
      operationId: getOrder
      responses:
        '200':
          description: OK
"""

FIXTURE_SQL_SCHEMA = """CREATE TABLE IF NOT EXISTS customers (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id CHAR(36) PRIMARY KEY,
    customer_id CHAR(36) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

FIXTURE_MARKDOWN_DOC = """# System Architecture Overview

## Services
The ecosystem includes `order-service` and `checkout-frontend`.

## API Endpoints
All client calls target `/api/v1/orders` and `/api/v1/health`.
Data is stored within `orders` and `customers` tables.
"""

FIXTURE_TERRAFORM_TF = """resource "aws_db_instance" "production_db" {
  engine         = "mysql"
  instance_class = "db.t3.medium"
  allocated_storage = 50
}

resource "aws_ecs_service" "orders_cluster" {
  name        = "orders-service"
  depends_on  = [aws_db_instance.production_db]
}
"""

FIXTURE_KUBERNETES_YAML = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-deployment
  namespace: production
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: app
          image: order-service:v1.1.0
          ports:
            - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: production
spec:
  ports:
    - port: 80
      targetPort: 8000
"""


def test_individual_parsers():
    """Verify all 10 parsers correctly extract normalized domain entities."""
    engine = IngestionEngine()

    # 1. package.json
    pkg_res = engine.parse_file("package.json", FIXTURE_PACKAGE_JSON)
    assert any(n.name == "checkout-frontend" and n.node_type == "service" for n in pkg_res.nodes)
    assert any(n.name == "react" and n.node_type == "component" for n in pkg_res.nodes)
    assert any(e.relationship_type == "depends_on" for e in pkg_res.edges)

    # 2. pyproject.toml
    pyproj_res = engine.parse_file("pyproject.toml", FIXTURE_PYPROJECT_TOML)
    assert any(n.name == "order-service" and n.node_type == "service" for n in pyproj_res.nodes)
    assert any(n.name == "fastapi" and n.node_type == "component" for n in pyproj_res.nodes)

    # 3. requirements.txt
    req_res = engine.parse_file("requirements.txt", FIXTURE_REQUIREMENTS_TXT)
    assert any(n.name == "pydantic" and n.node_type == "component" for n in req_res.nodes)

    # 4. Dockerfile
    docker_res = engine.parse_file("Dockerfile", FIXTURE_DOCKERFILE)
    assert any(n.node_type == "deployment" for n in docker_res.nodes)
    assert any(e.relationship_type == "deployed_as" for e in docker_res.edges)

    # 5. docker-compose.yml
    compose_res = engine.parse_file("docker-compose.yml", FIXTURE_DOCKER_COMPOSE)
    assert any(n.name == "web" and n.node_type == "service" for n in compose_res.nodes)
    assert any(n.name == "db" and n.node_type == "database" for n in compose_res.nodes)
    assert any(e.target_name == "db" and e.relationship_type == "depends_on" for e in compose_res.edges)

    # 6. OpenAPI
    openapi_res = engine.parse_file("openapi.yaml", FIXTURE_OPENAPI_YAML)
    assert any("GET /api/v1/orders" in n.name and n.node_type == "api" for n in openapi_res.nodes)
    assert any("POST /api/v1/orders" in n.name and n.node_type == "api" for n in openapi_res.nodes)

    # 7. SQL Schema
    sql_res = engine.parse_file("schema.sql", FIXTURE_SQL_SCHEMA)
    assert any(n.name == "customers" and n.node_type == "table" for n in sql_res.nodes)
    assert any(n.name == "orders" and n.node_type == "table" for n in sql_res.nodes)
    assert any(e.relationship_type == "contains" and e.target_name == "orders" for e in sql_res.edges)

    # 8. Markdown
    md_res = engine.parse_file("docs.md", FIXTURE_MARKDOWN_DOC)
    assert any(n.node_type == "documentation" for n in md_res.nodes)
    assert any(e.relationship_type == "documents" for e in md_res.edges)

    # 9. Terraform
    tf_res = engine.parse_file("main.tf", FIXTURE_TERRAFORM_TF)
    assert any("aws_db_instance" in n.name and n.node_type == "database" for n in tf_res.nodes)

    # 10. Kubernetes YAML
    k8s_res = engine.parse_file("k8s.yaml", FIXTURE_KUBERNETES_YAML)
    assert any("order-service-deployment" in n.name and n.node_type == "deployment" for n in k8s_res.nodes)
    assert any("order-service" in n.name and n.node_type == "service" for n in k8s_res.nodes)


@pytest.mark.asyncio
async def test_graph_api_endpoints_and_ingestion_pipeline(client: AsyncClient, test_session: AsyncSession):
    """Test full repository ingestion API, graph retrieval, node details, and statistics."""
    # Setup test org and repo
    org = Organization(name="Test Org")
    test_session.add(org)
    await test_session.flush()

    proj = Project(name="Test Proj", organization_id=org.id)
    test_session.add(proj)
    await test_session.flush()

    repo = Repository(name="ecommerce-core", url="https://github.com/org/ecom", project_id=proj.id)
    test_session.add(repo)
    await test_session.commit()

    # 1. Ingest multi-file payload
    files_payload = {
        "repository_id": str(repo.id),
        "repository_name": "ecommerce-core",
        "files": {
            "package.json": FIXTURE_PACKAGE_JSON,
            "pyproject.toml": FIXTURE_PYPROJECT_TOML,
            "docker-compose.yml": FIXTURE_DOCKER_COMPOSE,
            "openapi.yaml": FIXTURE_OPENAPI_YAML,
            "schema.sql": FIXTURE_SQL_SCHEMA,
            "architecture.md": FIXTURE_MARKDOWN_DOC,
        },
    }

    ingest_resp = await client.post("/api/v1/graph/ingest", json=files_payload)
    assert ingest_resp.status_code == 201
    ingest_data = ingest_resp.json()["data"]
    assert ingest_data["nodes_count"] > 10
    assert ingest_data["edges_count"] > 5

    # 2. Retrieve graph
    graph_resp = await client.get(f"/api/v1/graph?repository_id={repo.id}")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()["data"]
    assert graph_data["total_nodes"] == ingest_data["nodes_count"]
    assert graph_data["total_edges"] == ingest_data["edges_count"]

    first_node_id = graph_data["nodes"][0]["id"]

    # 3. Retrieve node details
    node_resp = await client.get(f"/api/v1/graph/nodes/{first_node_id}")
    assert node_resp.status_code == 200
    assert node_resp.json()["data"]["id"] == first_node_id

    # 4. Retrieve statistics
    stats_resp = await client.get("/api/v1/graph/statistics")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()["data"]
    assert stats_data["total_nodes"] > 0
    assert "service" in stats_data["nodes_by_type"]
    assert "table" in stats_data["nodes_by_type"]

    # 5. List relationships
    rel_resp = await client.get("/api/v1/graph/relationships?limit=50")
    assert rel_resp.status_code == 200
    assert len(rel_resp.json()["data"]) > 0
