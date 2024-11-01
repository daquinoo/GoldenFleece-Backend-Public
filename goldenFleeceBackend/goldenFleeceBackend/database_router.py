class AzureRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'api':
            return 'azure'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'api':
            return 'azure'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'api' or obj2._meta.app_label == 'api':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'api':
            return False  # Prevent migrations on the 'azure' database
        else:
            return db == 'default'
