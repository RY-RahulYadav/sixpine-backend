from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ReturnRequest, OrderStatusHistory
from .serializers import ReturnRequestSerializer, ReturnRequestCreateSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_return_request(request):
    """Submit a return request for an order item"""
    serializer = ReturnRequestCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        return_request = serializer.save()
        return Response(
            ReturnRequestSerializer(return_request).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_return_requests(request):
    """Get return requests for the authenticated user"""
    return_requests = ReturnRequest.objects.filter(
        order__user=request.user
    ).select_related('order', 'order_item__product', 'created_by').order_by('-created_at')
    
    serializer = ReturnRequestSerializer(return_requests, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_seller_return_requests(request):
    """Get return requests for products owned by the seller"""
    from accounts.models import Vendor
    
    try:
        vendor = request.user.vendor_profile
    except:
        return Response(
            {'error': 'User is not a vendor'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get return requests for products owned by this vendor
    return_requests = ReturnRequest.objects.filter(
        order_item__vendor=vendor
    ).select_related('order', 'order_item__product', 'order__user', 'created_by').order_by('-created_at')
    
    serializer = ReturnRequestSerializer(return_requests, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_return_request(request, return_request_id):
    """Approve or reject a return request (seller only)"""
    from accounts.models import Vendor
    
    try:
        vendor = request.user.vendor_profile
    except:
        return Response(
            {'error': 'User is not a vendor'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    return_request = get_object_or_404(
        ReturnRequest,
        id=return_request_id,
        order_item__vendor=vendor
    )
    
    approval_status = request.data.get('approval', None)
    seller_notes = request.data.get('seller_notes', '')
    
    if approval_status is None:
        return Response(
            {'error': 'approval field is required (true for approve, false for reject)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return_request.seller_approval = approval_status
    return_request.seller_notes = seller_notes
    return_request.approved_by = request.user
    
    if approval_status:
        return_request.status = 'approved'
        # Calculate refund amount (item price * quantity)
        refund_amount = return_request.order_item.price * return_request.order_item.quantity
        return_request.refund_amount = refund_amount
    else:
        return_request.status = 'rejected'
    
    return_request.save()
    
    # Create order status history
    OrderStatusHistory.objects.create(
        order=return_request.order,
        status='returned' if approval_status else return_request.order.status,
        notes=f'Return request {"approved" if approval_status else "rejected"} by seller',
        created_by=request.user
    )
    
    return Response(
        ReturnRequestSerializer(return_request).data,
        status=status.HTTP_200_OK
    )

