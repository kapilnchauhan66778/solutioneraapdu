from content_management import Content
from dbconnect import Connection
from MySQLdb import escape_string as thwart


def initial_indexing():

    TOPIC_ARRAY = Content()

    indexed = []
    for topic in TOPIC_ARRAY:
        try:
            indexed.append([topic[0], topic[1], topic[2], "Na", False])
            try:
                for bussiness in topic[3]:
                    indexed.append([bussiness[0], bussiness[1], bussiness[2], "Na", False])
                    try:
                        for product in bussiness[5]:
                            indexed.append([product[0], product[1], product[2], bussiness[1], True])
                    except:
                        pass
            except:
                pass
        except:
            pass

    return indexed

def index_things():

    indexed = initial_indexing()

    c, conn = Connection()

    c.execute("DELETE FROM indexed;")

    conn.commit()

    for t in indexed:
      c.execute("INSERT INTO indexed (HEADING, URL, IMG_URL, BUSINESS_OF_PRODUCT, PRODUCT) VALUES (%s, %s, %s, %s, %s);",
                               [thwart(str(t[0])), thwart(str(t[1])), thwart(str(t[2])), thwart(str(t[3])),thwart(str(int(t[4])))])

    

    conn.commit()

    c.close()
    conn.close()


def get_indexed_array(to_search):

    c, conn = Connection()

    c.execute("SELECT * FROM indexed where LOCATE((%s), HEADING) > 0;", [thwart(str(to_search))])

    indexed_array = list(([j for j in i[0:-1]] + [int(i[-1])]) for i in c.fetchall())

    conn.commit()

    c.close()
    conn.close()

    return indexed_array


# index_things()