import json
import logging
import pymysql
import pandas as pd

from SystemCode.configs.basic import LOG_LEVEL, FOOD_NUTRITION_CSV_PATH
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
                height INT,
                weight INT,
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
                AverageVolume DECIMAL(10, 2),
                AverageDensity DECIMAL(10, 2),
                DensityArea DECIMAL(10, 2)
            );

        """
        self.execute_query_(query, (), commit=True)

        query = """
            CREATE TABLE IF NOT EXISTS NutrientHistory (
                user_id VARCHAR(255),
                Datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FoodClasses VARCHAR(1024),
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
        
        self.init_food_nutrition()

    def check_user_exist_by_name(self, user_name):
        query = "SELECT user_name FROM User WHERE user_name = %s"
        result = self.execute_query_(query, (user_name,), fetch=True)
        return result is not None and len(result) > 0

    def add_user_(self, user_id, user_dict, user_name=None):
        # user_str = list(user_dict.values())
        user_str = [user_dict['height'], user_dict['weight'], user_dict['age'], user_dict['group'], user_dict['allergy']]
        query = "INSERT INTO User (user_id, user_name, height, weight, age, `group`, allergy) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.execute_query_(query, (user_id, user_name, user_str[0], user_str[1], user_str[2], user_str[3], user_str[4]), commit=True)
        return user_id

    def get_user_info(self, user_id):
        query = "SELECT * FROM User WHERE user_id = %s"
        result = self.execute_query_(query, (user_id,), fetch=True)
        return result

    def update_user_info(self, user_id, user_info_dict):
        allowed_fields = ['height', 'weight', 'age', 'group', 'allergy']
        set_clauses = []
        values = []

        for field in allowed_fields:
            if field in user_info_dict:
                if field == 'group':
                    set_clauses.append(f"`group` = %s")
                else:
                    set_clauses.append(f"{field} = %s")
                values.append(user_info_dict[field])

        if not set_clauses:
            return False

        set_clause = ", ".join(set_clauses)
        query = "UPDATE User SET {} WHERE user_id = %s".format(set_clause)
        values.append(user_id)
        self.execute_query_(query, values, commit=True)
        return True

    def init_food_nutrition(self):
        """ init food nutrition table """
        df = pd.read_csv(FOOD_NUTRITION_CSV_PATH)
        # drop some columns
        df.drop(df.columns[[0, 2, 12,]], axis=1, inplace=True)

        nutrition_data = df.values.tolist()

        query = """
            INSERT INTO FoodNutrient(Food_name, Calories, Protein, Fat, Carbs, Calcium, Iron, VC, VA, Fiber, 
            AverageVolume, AverageDensity, DensityArea)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query_(query, nutrition_data, commit=True, many=True)
        
    def check_user_exist_by_id(self, user_id):
        query = "SELECT user_id FROM User WHERE user_id = %s"
        result = self.execute_query_(query, (user_id,), fetch=True)
        return result is not None and len(result) > 0

    def add_history_(self, user_id, nutrition_dict):
        food_classes = json.dumps(nutrition_dict['food_dict'])
        nutrition_list = nutrition_dict['total_nutrition'].values()
        query = "INSERT INTO NutrientHistory (user_id, FoodClasses, Calories, Protein, Fat, Carbs, Calcium, Iron, VC, VA, Fiber) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.execute_query_(query, (user_id, food_classes, *nutrition_list), commit=True)
        return user_id

    def get_history_by_user_id(self, user_id, history_num):
        query = "SELECT * FROM NutrientHistory WHERE user_id = %s ORDER BY Datetime DESC LIMIT %s"
        result = self.execute_query_(query, (user_id, history_num), fetch=True)
        return result

    def get_chat_information(self, user_id):
        query = """
            SELECT height, weight, age, `group`, allergy
            FROM User
            WHERE user_id = %s;
        """
        results = self.execute_query_(query, (user_id,), fetch=True)
        return results

        
if __name__ == '__main__':
    client = MySQLClient()

