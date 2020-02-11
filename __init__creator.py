from content_management import Content

def create_init():
    TOPIC_ARRAY = Content()

    FUNC_TEMPLATE = '''

@app.route(TOPIC_ARRAY[sitter][1], methods=['GET', 'POST'])
def CURRENTTITLE():
    if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

    else:

        c, conn = Connection()

        c.execute("UPDATE services SET visit_count = visit_count + 1 WHERE service_url = (%s)", [thwart(str(TOPIC_ARRAY[sitter][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", TOPIC_ARRAY=TOPIC_ARRAY[sitter][3], url_for_image= TOPIC_ARRAY[sitter][2], main_topic=TOPIC_ARRAY[sitter][0])

    '''


    INNERFUNC_TEMPLATE = '''

@app.route(TOPIC_ARRAY[sitter][3][kapil][1], methods=['GET', 'POST'])
def CURRENTTITLE():
    if (request.method == 'POST'):
        try:
            money = request.form['money']
            HEADING = request.form['HEADING']
            IMAGE_URL = request.form['IMAGE_URL']
            
            c, conn = Connection()

            c.execute("UPDATE products SET visit_count = visit_count + 1 WHERE product_img_url = (%s) AND product_name = (%s) AND product_price = (%s)", [thwart(str(IMAGE_URL)), thwart(str(HEADING)), thwart(str(money))])
            conn.commit()

            c.execute("SELECT ph_num FROM businesses WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[sitter][3][kapil][1]))])

            ph_num = str(c.fetchall()[0][0])

            c.close()
            conn.close()

            return render_template('pricing.html',
                                   price=str(money),
                                   heading= HEADING,
                                   ph_num=ph_num)
                                   
        except:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)


    else:

        c, conn = Connection()

        c.execute("UPDATE businesses SET visit_count = visit_count + 1 WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[sitter][3][kapil][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", price=True, TOPIC_ARRAY=TOPIC_ARRAY[sitter][3][kapil][5], url_for_image= TOPIC_ARRAY[sitter][3][kapil][2] ,main_topic=TOPIC_ARRAY[sitter][3][kapil][0], ph_contact=TOPIC_ARRAY[sitter][3][kapil][3], email_contact=TOPIC_ARRAY[sitter][3][kapil][4])

    '''

    to_append = []

    with open("/var/www/FlaskApp/FlaskApp/__init__.py", "r") as f:
        lines = f.readlines()
        for INDEX, topic in enumerate(TOPIC_ARRAY):
            try:
                CURRENTTITLE = topic[0].replace("-","_").replace(" ","_").replace(",","").replace("/","").replace(")","").replace("(","").replace(".","").replace("!","").replace(":","-").replace("'","")
                if not f"def {CURRENTTITLE}():\n" in lines:
                    to_append.append(FUNC_TEMPLATE.replace("CURRENTTITLE",CURRENTTITLE).replace("sitter", str(INDEX)))

                for idxinner, inntopic in enumerate(topic[3]):
                    print(inntopic)
                    CURRENTTITLE = inntopic[0].replace("-","_").replace(" ","_").replace(",","").replace("/","").replace(")","").replace("(","").replace(".","").replace("!","").replace(":","-").replace("'","")
                    if not f"def {CURRENTTITLE}():\n" in lines:
                        print(str(idxinner))
                        to_append.append(INNERFUNC_TEMPLATE.replace("CURRENTTITLE",CURRENTTITLE).replace("sitter", str(INDEX)).replace("kapil", str(idxinner)))

            except Exception as e:
                print(str(e))

    for i in to_append:
        with open("/var/www/FlaskApp/FlaskApp/__init__.py", "a") as f:
            print(i)
            f.write(i)

# create_init()
