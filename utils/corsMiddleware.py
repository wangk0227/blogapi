from django.utils.deprecation import MiddlewareMixin




class Cors(MiddlewareMixin):
    def process_response(self, request, response):
        response["Access-Control-Allow-Origin"] = "*"
        if request.method == "OPTIONS":
            response[
                "Access-Control-Allow-Headers"] = "Content-Type, AcceptToken,Origin, X-Requested-With,"  # 请求头要放开 前端token使用什么就要放开什么

            response["Access-Control-Allow-Methods"] = "DELETE, PUT, POST"
        return response
