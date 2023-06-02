from asyncio.log import logger
from datetime import datetime,timedelta
import psycopg2
from dotenv import load_dotenv
import redis
import loguru
from traceback import  format_exc

import json
import os

ENV_DIR = os.path.join(os.getcwd(),'.env')
load_dotenv(ENV_DIR)
log = loguru.logger

COLUMNS_NAME = [
    'id', 'event_name', 'event_type', 'user_id', 'wallet_address', 
    'insert_id', 'timestamp', 'app_version', 'event_properties', 
    'browser_type', 'os_name', 'os_version', 'device_type', 
    'auto_track_timestamp', 'url', 'referrer', 'country', 
    'language', 'user_properties', 'environment_type'
    ]

def db_proccess(name,values):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=name,
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PWD"),
        )
        conn.autocommit = True
        log.info("Db connected")
        cur = conn.cursor()
        # test
        
        
        #
        cur.execute(f"select column_name from information_schema.columns where table_name = 'events';")
        current_columns = [x[0] for x in cur.fetchall()]
        for column in current_columns:
            if column not in COLUMNS_NAME:
                cur.execute(f"alter table events drop column {column};")
                conn.commit()
    
    except (Exception, psycopg2.OperationalError) as error:
        conn = None
        try:
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                database="",
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PWD"),
            )
            conn.autocommit = True
            log.info("Db connected")
            cur = conn.cursor()
            cur.execute(f'CREATE DATABASE {name}')
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {name} TO {os.environ.get('DB_USER')};")
            conn.close()

            conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=name,
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PWD"),
            )
            conn.autocommit = True
            log.info("Db connected")
            cur = conn.cursor()

        except (Exception, psycopg2.DatabaseError) as error:
            log.debug("Some error ")
            return
    finally:
        try:
            cur.execute("ALTER TABLE events ADD environment_type VARCHAR (200) default ''")
            conn.commit()
        except:
            pass
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id serial PRIMARY KEY,
                event_name VARCHAR (355) NOT NULL,
                event_type VARCHAR (50) NOT NULL,
                user_id INTEGER NOT NULL,
                wallet_address VARCHAR (50) NOT NULL,
                insert_id INTEGER NOT NULL,
                timestamp BIGINT NOT NULL,
                app_version VARCHAR (50) NOT NULL,
                event_properties json NOT NULL,
                browser_type VARCHAR (250) NOT NULL,
                os_name VARCHAR (250) NOT NULL,
                os_version VARCHAR (250) NOT NULL,
                device_type VARCHAR (250) NOT NULL,
                auto_track_timestamp BIGINT NOT NULL,
                url VARCHAR (250) NOT NULL,
                referrer VARCHAR (250) NOT NULL,
                country VARCHAR (250) NOT NULL,
                language VARCHAR (250) NOT NULL,
                user_properties json NOT NULL,
                environment_type VARCHAR (200)

            );
        """)

        conn.commit()

        log.info("Db proccess next")
        if values[4] == 0:
            query = """insert into events (
                event_name,event_type,user_id,wallet_address,insert_id,
                timestamp,app_version,event_properties,browser_type,
                os_name,os_version,device_type,auto_track_timestamp,
                url,referrer,country,language,user_properties,environment_type
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cur.execute(query,values)
            conn.commit()
        else:
            delta = int((datetime.now() - timedelta(days=7) ).timestamp())
            cur.execute(f"SELECT * FROM events where insert_id = '{values[4]}' and auto_track_timestamp > '{delta}'")
            if cur.fetchall() == []:
                query = """insert into events (
                event_name,event_type,user_id,wallet_address,insert_id,
                timestamp,app_version,event_properties,browser_type,
                os_name,os_version,device_type,auto_track_timestamp,
                url,referrer,country,language,user_properties,environment_type
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                cur.execute(query,values)
                conn.commit()
            else: 
                log.info("Db execute Done")
                cur.close()
                return        

        log.info("Db execute Done")
        cur.close()





def red_is(r):
    res : dict
    keys = r.keys()
    log.info(keys)
    for elem in keys:
        try:
            res = json.loads(r.get(elem))
            if res :
                values = (
                    res.get("event_name",""),
                    res.get("event_type",""),
                    int(res["user_ids"].get("user_id","")),
                    res["user_ids"].get("wallet_address",""),
                    int(res["other_admin_variables"].get("insert_id",0)),
                    int(res["other_admin_variables"].get("timestamp",0)),
                    res["other_admin_variables"].get("app_version",""),
                    json.dumps(res.get("event_properties",{})),
                    res["automatically_tracked"].get("browser_type",""),
                    res["automatically_tracked"].get("os_name",""),
                    res["automatically_tracked"].get("os_version",""),
                    res["automatically_tracked"].get("device_type",""),
                    int(res["automatically_tracked"].get("timestamp",0)),
                    res["automatically_tracked"].get("url",""),
                    res["automatically_tracked"].get("referrer",""),
                    res["automatically_tracked"].get("country",""),
                    res["automatically_tracked"].get("language",""),
                    json.dumps(res.get("user_properties",{})),
                    res.get("environment_type",""),
                )
                r.delete(elem)
                name = elem.split("_counter_")[0].lower()
                db_proccess(name,values)
        except:
            pass


def main():

    log.info("Start")
    r = redis.Redis(host=os.environ.get("REDIS_IP"), port=int(os.environ.get("REDIS_PORT")), db=0, decode_responses=True)
    log.info("Redis connected")
    red_is(r)
    log.info("End process")


if __name__ == '__main__':
    main()



# execute a statement
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS app_user (
        #         id serial PRIMARY KEY,
        #         event_name VARCHAR (355) UNIQUE NOT NULL,
        #         event_type VARCHAR (50) NOT NULL,
        #         user_id VARCHAR (50) NOT NULL,
        #         wallet_address VARCHAR (50) NOT NULL,
        #         insert_id VARCHAR (50) NOT NULL,
        #         timestamp VARCHAR (50) NOT NULL,
        #         app_version VARCHAR (50) NOT NULL,
        #         event_properties json NOT NULL,
        #         browser_type VARCHAR (250) NOT NULL,
        #         os_name VARCHAR (250) NOT NULL,
        #         os_version VARCHAR (250) NOT NULL,
        #         device_type VARCHAR (250) NOT NULL,
        #         auto_track_timestamp VARCHAR (250) NOT NULL,
        #         url VARCHAR (250) NOT NULL,
        #         referrer VARCHAR (250) NOT NULL,
        #         country VARCHAR (250) NOT NULL,
        #         language VARCHAR (250) NOT NULL,
        #         user_properties json NOT NULL
        #     );
        # """)


