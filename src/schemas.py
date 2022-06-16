from src import ma
from marshmallow import fields


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'email', 'password', 'uuid', 'registered_date', 'current_login', 'last_login', 'userpic', 'is_admin')
        load_only = ['password']
    name = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)


class IngridientSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'recipes')
    recipes = ma.Nested('RecipeSchema', many=True, exclude=('ingridients',))


class RecipeSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'recipe', 'ingridients')
    ingridients = ma.Nested('IngridientSchema', many=True, exclude=('recipes',))


class FeedbackSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'message', 'date_time')
    name = fields.String(required=True)
    message = fields.String(required=True)


class TrackerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'ipaddress', 'city', 'country', 'date_time', 'action')


class RecipeFeedbackSchema(ma.Schema):
    class Meta:
        fields = ('id', 'recipe_id', 'user_id', 'message', 'ip', 'date_time')
    message = fields.String(required=True)
    recipe = ma.Nested(RecipeSchema)
    user = ma.Nested(UserSchema)
