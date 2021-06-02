#  mysql connection settings
# TODO move config file to top directory
class config:
    host = 'capo.guide'
    dev_host = '192.168.1.69'

    image_config = dict(
        host='http://'+'assets.'+host,

        # * deprecated
        img_server_port='8082',
        img_handler_port='8083',
    )

    db_conf = dict(
        host = "db."+host,
        user='user',
        password='onebillion',
        db_name='gigit_db_dev',
        port=3306
    )


    
    