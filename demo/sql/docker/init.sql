CREATE DATABASE demo CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'demo_u' IDENTIFIED WITH mysql_native_password BY 'password';
GRANT ALL PRIVILEGES ON demo.* TO 'demo_u';
-- Need to grant access to test database even though we don't create it until running the tests
GRANT ALL PRIVILEGES ON test_demo.* TO 'demo_u';
