import SimpleService_pb2 as pb2
import SimpleService_pb2_grpc as pb2_grpc

class SimpleHandler(pb2_grpc.SimpleServiceServicer):
    def GetServerResponse(self, request, context):
        
        msg = request.message
        reply = {"message": msg, "received": True}
        
        return pb2.MessageResponse(**reply)