from datetime import datetime
from models.product_variant_model import ProductVariantModel


class ProductVariantsDB:
    def __init__(self, pool):
        self.pool = pool

    async def create_variant(self, variant: ProductVariantModel):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                INSERT INTO product_variants (barcode, product_id, come_in_price, current_price, old_price, discount, 
                                              is_main, amount, weight, color_id, size_id, measure_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id;
                """
                return await conn.fetchval(
                    query, variant.barcode, variant.product_id, variant.come_in_price, variant.current_price,
                    variant.old_price, variant.discount, variant.is_main, variant.amount, variant.weight,
                    variant.color_id, variant.size_id, variant.measure_id, datetime.utcnow(), datetime.utcnow()
                )

    async def update_variant(self, variant_id: int, variant: ProductVariantModel):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = """
                UPDATE product_variants
                SET barcode = $1, product_id = $2, come_in_price = $3, current_price = $4, old_price = $5, discount = $6, 
                    is_main = $7, amount = $8, weight = $9, color_id = $10, size_id = $11, measure_id = $12, updated_at = $13
                WHERE id = $14;
                """
                await conn.execute(
                    query, variant.barcode, variant.product_id, variant.come_in_price, variant.current_price,
                    variant.old_price, variant.discount, variant.is_main, variant.amount, variant.weight,
                    variant.color_id, variant.size_id, variant.measure_id, datetime.utcnow(), variant_id
                )
                return {"message": "Variant updated successfully"}

    async def delete_variant(self, variant_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query = "DELETE FROM product_variants WHERE id = $1;"
                await conn.execute(query, variant_id)
                return {"message": "Variant deleted successfully"}

    async def get_variant(self, variant_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM product_variants WHERE id = $1;"
            row = await conn.fetchrow(query, variant_id)
            return ProductVariantModel(**dict(row)) if row else None

    async def get_variants_by_product(self, product_id: int):
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM product_variants WHERE product_id = $1;"
            rows = await conn.fetch(query, product_id)
            return [ProductVariantModel(**dict(row)) for row in rows]
