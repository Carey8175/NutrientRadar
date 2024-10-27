import logging
import pymysql

from SystemCode.configs.basic import LOG_LEVEL
from SystemCode.configs.database import *


# ----------------- Logger -----------------
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', force=True)


class MySQLClient:
    def __init__(self):
        self.host = MYSQL_HOST
        self.port = MYSQL_PORT
        self.user = MYSQL_USER
        self.password = MYSQL_PASSWORD
        self.database = MYSQL_DATABASE
        self._check_connection()

        db_config = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
        }

        # self.conn_pool = MySQLThreadPool(MAX_CONNECTIONS, db_config=db_config)

    def get_conn(self):
        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )

        return conn

    def _check_connection(self):
        # connect to mysql
        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password
        )
        cursor = conn.cursor()
        cursor.execute('SHOW DATABASES')
        databases = [database[0] for database in cursor]

        if self.database not in databases:
            # 如果数据库不存在，则新建数据库
            cursor.execute('CREATE DATABASE IF NOT EXISTS {}'.format(self.database))
            logging.debug("数据库{}新建成功或已存在".format(self.database))
            self.create_tables_()
        logging.info("[SUCCESS] 数据库{}检查通过".format(self.database))

        cursor.close()
        conn.close()

    def execute_query_(self, query, params, commit=False, fetch=False, many=False):
        # conn = self.conn_pool.get_connection()
        conn = self.get_conn()
        cursor = conn.cursor()

        if many:
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)

        if commit:
            conn.commit()

        if fetch:
            result = cursor.fetchall()
        else:
            result = None

        cursor.close()
        # self.conn_pool.release_connection(conn)
        conn.close()
        logging.info("[SUCCESS] Query executed successfully with sql: {} \n".format(query))

        return result

    def create_tables_(self):
        query = """
            CREATE TABLE IF NOT EXISTS User (
                user_id VARCHAR(255) PRIMARY KEY,
                user_name VARCHAR(255),
                api_key VARCHAR(255),
                base_url VARCHAR(255),
                model VARCHAR(255),
                height INT,
                width INT,
                age INT,
                `group` VARCHAR(255),
                allergy VARCHAR(255)
            );
        """
        self.execute_query_(query, (), commit=True)

        query = """
            CREATE TABLE IF NOT EXISTS FoodNutrient(
                Food_name VARCHAR(255) PRIMARY KEY,
                Calories DECIMAL(10, 2),
                Protein DECIMAL(10, 2),
                Fat  DECIMAL(10, 2),
                Carbs DECIMAL(10, 2),
                Calcium DECIMAL(10, 2),
                Iron DECIMAL(10, 2),
                VC DECIMAL(10, 2),
                VA DECIMAL(10, 2),
                Fiber DECIMAL(10, 2),
                DensityArea DECIMAL(10, 2)
            );

        """
        self.execute_query_(query, (), commit=True)

        query = """
            CREATE TABLE IF NOT EXISTS NutrientHistory (
                user_id VARCHAR(255) PRIMARY KEY,
                Datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FoodClasses VARCHAR(255),
                Calories DECIMAL(10, 2),
                Protein DECIMAL(10, 2),
                Fat  DECIMAL(10, 2),
                Carbs DECIMAL(10, 2),
                Calcium DECIMAL(10, 2),
                Iron DECIMAL(10, 2),
                VC DECIMAL(10, 2),
                VA DECIMAL(10, 2),
                Fiber DECIMAL(10, 2),
                FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
            );
        """
        self.execute_query_(query, (), commit=True)


if __name__ == '__main__':
    client = MySQLClient()


