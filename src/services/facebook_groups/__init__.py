from src.services.facebook_groups.models import FacebookGroup
from src.services.facebook_groups.bl import FacebookGroupBL

# Re-export commonly used methods for convenience
get_group = FacebookGroupBL.get_group
get_all_groups = FacebookGroupBL.get_all_groups
get_active_groups = FacebookGroupBL.get_active_groups
create_or_update_group = FacebookGroupBL.create_or_update_group
set_group_active = FacebookGroupBL.set_group_active
remove_group = FacebookGroupBL.remove_group
update_group_metadata = FacebookGroupBL.update_group_metadata
import_groups_from_config = FacebookGroupBL.import_groups_from_config 