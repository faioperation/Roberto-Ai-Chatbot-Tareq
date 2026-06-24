from agent.tools.search_knowledge import search_knowledge
from agent.tools.handoff_human import handoff_human
from agent.tools.collect_lead import make_collect_lead
from agent.tools.create_booking import make_create_booking
from agent.tools.get_pricing import make_get_pricing


def get_all_tools(business_id: str = None, branch_id: str = None, channel: str = None):
    return [
        search_knowledge,
        handoff_human,
        make_collect_lead(branch_id, channel),
        make_create_booking(branch_id),
        make_get_pricing(business_id, branch_id),
    ]