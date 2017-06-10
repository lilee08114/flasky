from flask import Blueprint

reg = Blueprint('reg', __name__)
from . import views,error   #在自定视图和错误处理函数后，将其导入构造文件，
							#因为蓝本创建于此，就可以将蓝本和视图关联起来