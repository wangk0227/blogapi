import sys,os
import pymysql
pymysql.install_as_MySQLdb()
path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(path)


