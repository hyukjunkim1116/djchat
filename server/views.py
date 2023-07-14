from django.db.models import Count
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from .models import Server
from .schema import server_list_docs
from .serializer import ServerSerializer


class ServerListViewSet(viewsets.ViewSet):
    queryset = Server.objects.all()

    @server_list_docs
    def list(self, request):
        """
        Retrieves a list of servers based on the provided query parameters.
        """
        # Get query parameters
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"

        # Check if user authentication is required

        # Filter queryset based on category
        if category:
            self.queryset = self.queryset.filter(category__name=category)

        # Filter queryset based on the requesting user
        if by_user:
            if request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)
            else:
                raise AuthenticationFailed()

        # Annotate queryset with the number of members
        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        # Limit the queryset based on the specified quantity
        if qty:
            self.queryset = self.queryset[: int(qty)]

        # Filter queryset based on server ID
        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()

            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server ID {by_serverid} not found")
            except ValueError:
                raise ValidationError(detail="Server value error.")

        # Serialize queryset and return the response
        serializer = ServerSerializer(
            self.queryset, many=True, context={"num_members": with_num_members}
        )
        return Response(serializer.data)
