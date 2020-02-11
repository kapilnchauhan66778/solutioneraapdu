import MySQLdb

def Connection():
    conn = MySQLdb.connect(host="localhost",
                           user = "root",
                           passwd = "Tigerman@77",
                           db = "solutionera")
    c = conn.cursor()
    return c, conn
