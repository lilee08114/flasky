from .m import create_app
web = create_app()
print (type(web))
if __name__ == '__main__':
	web.run()
