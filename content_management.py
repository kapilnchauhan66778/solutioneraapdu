from dbconnect import Connection
from MySQLdb import escape_string as thwart

def Content_build_for_my_sql():

    ##############################################################          EXPLAINTION FOR ME          ################################################################################################
    # [
    #     [
    #         TOPIC NAME,
    #         TOPIC URL,
    #         TOPIC IMAGE, 
    #                     [
    #                         [
    #                             BUSINESS IN THAT TOPIC NAME,
    #                             BUSINESS IN THAT TOPIC URL,
    #                             BUSINESS IN THAT TOPIC Image,
    #                             BUSINESS IN THAT TOPIC CONTANT NUMBER,
    #                             BUSINESS IN THAT TOPIC CONTACT EMAIL,
    #                             [BUSINESS IN THAT TOPIC IMAGES TO DISPLAY],
    #                                                                         [
    #                                                                             [
    #                                                                                 SERVICE OFFERED BY THE BUSINESS NAME,
    #                                                                                 SERVICE OFFERED BY THE BUSINESS URL,
    #                                                                                 SERVICE OFFERED BY THE BUSINESS IMAGE,
    #                                                                                 SERVICE OFFERED BY THE BUSINESS PRICE
    #                                                                                                                         ], 
    #                                                                                                                             ] 
    #                                                                                                                                ], 
    #                                                                                                                                    ]
    #                                                                                                                                       ],
    #                                                                                                                                           ]

    topic_array = [
                    [
                        "Tuition Classes", 
                        "/tuition/", 
                        "http://www.kiplinger.com/kipimages/pages/18048.jpg",
                        [
                            [
                                "Shubham Classes",
                                "/Shubham_Classes/",
                                "http://www.kiplinger.com/kipimages/pages/18048.jpg",
                                "+917984147792",
                                "XYZ@gmail.com",
                                [
                                   ["Std 10th to 12th",
                                    "Rs. 500",
                                    "http://netdna.webdesignerdepot.com/uploads/2013/11/picjumbo.com_IMG_9857.jpg"]
                                ]
                            ],
                            [
                                "Science Tuition", 
                                "/Science_Tuition/",
                                "http://netdna.webdesignerdepot.com/uploads/2013/11/picjumbo.com_IMG_9857.jpg",
                                "+917069361889",
                                "ABC@gmail.com",
                                [
                                    []
                                ]
                            ],
                            [
                                "Math Tuition",
                                "/Math_Tuition/",
                                "http://www.kiplinger.com/kipimages/pages/18048.jpg",
                                "+919173601206",
                                "ZZZ@gmail.com",
                                [
                                    []
                                ]
                            ]
                        ]
                    ],
                    [
                        "Electricians",
                        "/electrician/",
                        "http://netdna.webdesignerdepot.com/uploads/2013/11/picjumbo.com_IMG_9857.jpg",
                        [
                            []
                        ]
                    ]
                  ]

    return topic_array


def my_sql_build_from_content():
    topic_array = Content_build_for_my_sql()

    try:
        c, conn = Connection()

        c.execute("SELECT SID FROM services")

        fetched = c.fetchall()

        if list(fetched):
            SID = fetched[-1][0]
        else:
            SID = 0
        for topic in topic_array:
            try:
                service_name = topic[0]
                service_url = topic[1]
                service_img_url = topic[2]
                SID += 1
                visit_count = 0
                services_previously_in_db = c.execute("SELECT * FROM services WHERE service_url = (%s)", [thwart(str(service_url)),])
                if not int(services_previously_in_db) > 0:
                    print([service_name, service_url, service_img_url, SID, visit_count])
                    c.execute("INSERT INTO services (service_name, service_url, service_img_url, visit_count) VALUES (%s, %s, %s, %s);",
                     [thwart(str(service_name)), thwart(str(service_url)), thwart(str(service_img_url)), 0,])
                c.execute("SELECT BID FROM businesses;")
                if list(fetched):
                    BID = fetched[-1][0]
                else:
                    BID = 0
                for service in topic[3]:
                    try:
                        business_name = service[0]
                        business_url = service[1]
                        business_img_url = service[2]
                        ph_num = service[3]
                        email_id = service[4]
                        BID += 1
                        visit_count = 0
                        businesses_previously_in_db = c.execute("SELECT * FROM businesses WHERE business_url = (%s)", [thwart(str(business_url)),])
                        if not int(businesses_previously_in_db) > 0:
                            print([SID, business_name, business_url, business_img_url, ph_num, email_id, BID, visit_count])
                            c.execute("INSERT INTO businesses (SID, business_name, business_url, business_img_url, ph_num, email_id, visit_count) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                             [thwart(str(SID)), thwart(str(business_name)), thwart(str(business_url)), thwart(str(business_img_url)), thwart(str(ph_num)), thwart(str(email_id)), 0,])
                        for product in service[5]:
                            try:
                                product_name = product[0]
                                product_price = product[1]
                                product_img_url = product[2]
                                visit_count = 0
                                products_previously_in_db = c.execute("SELECT * FROM products WHERE product_img_url = (%s) AND product_name = (%s) AND product_price = (%s)", [thwart(str(product_img_url)), thwart(str(product_name)), thwart(str(product_price)),])
                                if not int(products_previously_in_db) > 0:
                                    print([BID, product_name, product_price, product_img_url, visit_count])
                                    c.execute("INSERT INTO products (BID, product_name, product_price, product_img_url, visit_count) VALUES (%s, %s, %s, %s, %s);",
                                     [thwart(str(BID)), thwart(str(product_name)), thwart(str(product_price)), thwart(str(product_img_url)), 0,])
                            except:
                                pass
                    except:
                        pass
            except:
                pass

        conn.commit()
        c.close()
        conn.close()
    except:
        conn.commit()
        c.close()
        conn.close()



def Content():
    c, conn = Connection()

    c.execute("SELECT service_name, service_url, service_img_url, SID FROM services")

    services = list(list(i) for i in c.fetchall())

    for service in services:
        sid = service[-1]


        service[-1] = []

        c.execute("SELECT business_name, business_url, business_img_url, ph_num, email_id, BID FROM businesses WHERE SID = (%s)", [thwart(str(sid))])

        businesses_offering_the_service = c.fetchall()

        if businesses_offering_the_service:
            for business in businesses_offering_the_service:
                business = list(business)

                bid = business[-1]

                business[-1] = []

                c.execute("SELECT product_name, product_price, product_img_url FROM products WHERE BID = (%s)", [thwart(str(bid))])

                products_offered_by_the_business = c.fetchall()

                if products_offered_by_the_business:
                    for product in products_offered_by_the_business:
                        product = list(product)
                        business[-1].append(product)
                else:
                    business[-1].append([])

                service[-1].append(business)

        else:
            service[-1].append([])

    c.close()
    conn.close()

    return services

# my_sql_build_from_content()
# print(Content_build_for_my_sql() == Content())
