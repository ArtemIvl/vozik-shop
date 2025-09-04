from alembic import op
import sqlalchemy as sa


revision = '695ab68c42de'
down_revision = '3cced56598b2'
branch_labels = None
depends_on = None

language_enum = sa.Enum('EN', 'RU', 'UA', name='language', native_enum=True)


def upgrade():
    # Создаём ENUM
    language_enum.create(op.get_bind(), checkfirst=True)

    # ALTER TABLE с указанием преобразования
    op.execute("ALTER TABLE users ALTER COLUMN language TYPE language USING language::language")


def downgrade():
    op.execute("ALTER TABLE users ALTER COLUMN language TYPE VARCHAR(2)")
    language_enum.drop(op.get_bind(), checkfirst=True)