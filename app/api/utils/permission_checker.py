from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.user import AdminUser
from app.api.models.warehouse import AdminWarehouse, Warehouse, admin_warehouse_roles


async def check_permission(
        session: AsyncSession,
        admin_id: int,
        model_name: str,
        action: str,
        warehouse_id: int = None,
) -> bool:
    """
    Foydalanuvchining berilgan warehouse_id va model_name uchun ruxsatini tekshiradi.

    :param session: AsyncSession - Ma'lumotlar bazasi sessiyasi.
    :param admin_id: int - Foydalanuvchi (admin) IDsi.
    :param warehouse_id: int - Warehouse IDsi.
    :param model_name: str - Model nomi (masalan, "measure", "product").
    :param action: str - Amal nomi (masalan, "read", "create").
    :return: bool - Ruxsat mavjud bo'lsa True, aks holda exception.
    """
    # AdminWarehouse va Warehouse ma'lumotlarini olish

    admin = await session.get(AdminUser, admin_id)
    if admin and admin.is_global_admin:
        return True

    query = (
        select(AdminWarehouse)
        .join(
            admin_warehouse_roles,
            AdminWarehouse.id == admin_warehouse_roles.c.warehouse_role_id,
        )
        .where(
            admin_warehouse_roles.c.admin_id == admin_id,
            AdminWarehouse.warehouse_id == warehouse_id,
        )
    )

    result = await session.execute(query)
    admin_warehouse = result.scalar_one_or_none()

    # Agar admin warehouse ga ruxsati yo'q bo'lsa
    if not admin_warehouse:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No access to warehouse {warehouse_id}",
        )

    # Agar admin warehouse owner bo'lsa, hamma ruxsatlar beriladi
    if admin_warehouse.is_owner:
        return True

    # Global admin tekshiruvi
    warehouse = await session.get(Warehouse, warehouse_id)
    if warehouse and warehouse.owner_id == admin_id:
        return True

    # Ruxsatlarni tekshirish
    permissions = admin_warehouse.permissions
    if not permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No permissions found for warehouse {warehouse_id}",
        )

    # "all" ruxsatlari tekshiruvi
    if "all" in permissions and action in permissions["all"]:
        return True

    # Model uchun ruxsatlar tekshiruvi
    if model_name not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No permissions for {model_name}",
        )

    # Action uchun ruxsat tekshiruvi
    if action not in permissions[model_name]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No {action} permission for {model_name}",
        )

    return True
