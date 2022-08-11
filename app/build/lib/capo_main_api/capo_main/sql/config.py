# TODO move config file to top directory
class Config:
    __conf = {
        'images': {
            'api_host': '',
            'server_host': ''
        },

        'db': {
            'host': '',
            'user': 'user',
            'password': 'onebillion',
            'db_name': 'gigit_db_dev',
            'port': 3307
        },
        'env': ''
    }

    @staticmethod
    def get(name):
        return Config.__conf[name]

    @staticmethod
    def set_env(_env):
        prod_host = 'capo.guide'

        images_api_port = 12123
        images_server_port = 12124

        if _env == 'dev':

            images_host = 'dev.images.'+prod_host+':'+str(images_api_port)
            images_server_host = 'dev.assets.'+prod_host+':'+str(images_server_port)

            db_host = 'dev.db.'+prod_host

            env = _env

            print('Running in dev mode')
            print('Using dev URI for images, assets, database')
            print('images_host: {}\nassets_host: {}\ndb_host: {}'.format(images_host, images_server_host, db_host+':3307'))

        elif _env == 'prod':
            images_host = 'images.'+prod_host
            images_server_host = 'assets.'+prod_host
            db_host = 'db.'+prod_host

            env = _env

        else:
            raise Exception('Not a recognised env')

        Config.__conf['images']['api_host'] = 'https://'+images_host
        Config.__conf['images']['server_host'] = 'https://'+images_server_host
        Config.__conf['db']['host'] = db_host
        Config.__conf['env'] = env


    
    