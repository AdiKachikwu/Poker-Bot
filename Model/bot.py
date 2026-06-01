"""
╔══════════════════════════════════════════════════════════════╗
║         FULLHOUSE HACKATHON — BOT TEMPLATE v1.0             ║
║         No-Limit Texas Hold'em, 6-max                        ║
╚══════════════════════════════════════════════════════════════╝

RULES:
  - Implement the decide() function below. That's it.
  - You may import any stdlib module and any library in requirements.txt
  - You have 2 seconds to return an action or you auto-fold
  - If your function crashes, it auto-folds for that hand

NOT ALLOWED (will DQ your bot):
  - External API calls: no Claude/OpenAI/Anthropic/Google/any HTTP. Network is
    blocked at the container level; trying anyway is a DQ.
  - File writes during gameplay; data/ is read-only and only at import time.
  - subprocess / os.system / shell commands.
  - Threading or async tricks to dodge the 2s/action signal timer.
  - Reflection: __import__('socket'), getattr(__builtins__, 'open'),
    eval(), exec(), compile() — all flagged by the validator.
  - Collusion between bots you've registered with friends — bots must play
    independently; coordinated soft-play or chip-dumping = both DQ'd.
  - Reading other bots' code or hole cards (you can't anyway, but trying = DQ).

OPTIONAL DATA FILES (NEW):
  Submit a .zip archive containing:
    bot.py        (this file, required at root)
    data/         (optional directory with .npz, .pkl, .bin, etc.)

  At module-import time only, you can read from a sibling 'data/' directory:

      import os
      DATA_DIR = os.environ.get("BOT_DATA_DIR",
                                os.path.join(os.path.dirname(__file__), "data"))
      with open(os.path.join(DATA_DIR, "blueprint.npz"), "rb") as f:
          BLUEPRINT = ...load(f)

  Limits:
    - Total submission (bot.py + data/) <= 250 MB
    - data/ alone <= 200 MB
    - bot.py <= 5 MB
    - File access during decide() is blocked at the OS level

CARD FORMAT:
  Cards are strings like "As" (Ace of spades), "Td" (Ten of diamonds)
  Ranks: 2 3 4 5 6 7 8 9 T J Q K A
  Suits: s (spades) h (hearts) d (diamonds) c (clubs)

RETURN FORMAT:
  {"action": "fold"}
  {"action": "check"}          # only valid when amount_owed == 0
  {"action": "call"}
  {"action": "raise", "amount": 1200}   # amount = TOTAL bet, not raise-by
  {"action": "all_in"}

  Invalid actions default to fold. Raises below min_raise_to are snapped up.
"""

# ── You may add imports here ──────────────────────────────────────────────────
import random
import os
import pickle

from pyexpat import features

#Upload the Brain

data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(data_dir, "tree.pkl"), "rb") as f:
    model = pickle.load(f)
# ─────────────────────────────────────────────────────────────────────────────

BOT_NAME = "King_Poker"          # Show name on the leaderboard
BOT_AVATAR = "robot_1"      # Chosen in the portal, not here

#Functions
def get_hand_strength(cards):
    rank_order = "23456789TJQKA"
    values = [rank_order.index(c[0]) for c in cards]
    return sum(values)/len(values) * 12

def stage_to_integer(street):
    return {
        "preflop": 0 ,
        "flop": 1,
        "turn": 2 ,
        "river": 3
    }[street]


def decide(game_state: dict) -> dict:
    """
    Called once per action. Must return within 2 seconds.

    game_state keys:
      hand_id          str   — unique hand identifier
      street           str   — "preflop" | "flop" | "turn" | "river"
      seat_to_act      int   — your seat number (0-5)
      pot              int   — total chips in pot
      community_cards  list  — e.g. ["As", "Kd", "7h"] (empty preflop)
      current_bet      int   — highest bet on this street
      min_raise_to     int   — minimum legal raise total
      amount_owed      int   — chips you need to put in to call (0 = free check)
      can_check        bool  — True when amount_owed == 0
      your_cards       list  — your two hole cards, e.g. ["Ah", "Kh"]
      your_stack       int   — your remaining chips
      your_bet_this_street int — chips you've already put in this street
      players          list  — public info on all seats (see below)
      action_log       list  — all actions so far this hand

    players[i] keys (public info only, no hole cards):
      seat, bot_id, stack, is_active, is_folded, is_all_in, bet_this_street
    """

    # ── Your strategy goes here ───────────────────────────────────────────────




    my_cards = game_state["your_cards"]
    community_cards = game_state["community_cards"]
    all_cards = my_cards + community_cards

    hand_strength = get_hand_strength(all_cards)
    position = game_state["seat_to_act"]
    pot = game_state["pot"]
    current_bet = game_state["current_bet"]
    stack = game_state["your_stack"]
    amount_owed = game_state["amount_owed"]

    active_players = sum(1 for p in game_state["players"] if p["active"])
    stage = stage_to_integer(game_state["street"])

    # Pocket aces or kings — raise big
    ranks = [c[0] for c in my_cards]
    if ranks.count("A") == 2 or ranks.count("K") == 2:
        raise_to = min(pot * 3, stack + game_state["your_bet_this_street"])
        raise_to = max(raise_to, game_state["min_raise_to"])
        return {"action": "raise", "amount": raise_to}

    # Free check — always take it
    if game_state["can_check"]:
        return {"action": "check"}

    #Random Bluff
    if hand_strength < 0.3 and random.random() < 0.9:
        raise_to = max(game_state["min_raise_to"], pot)
        return {"action": "raise", "amount": raise_to}

    #Model
    features = [[hand_strength, current_bet, pot, active_players, stage ]]
    action = model.predict(features)[0]

    if action == "raise":
        raise_to = min(pot * 2, stack + game_state["your_bet_this_street"])
        raise_to = max(raise_to, game_state["min_raise_to"])
        return {"action": "raise", "amount": raise_to}

    elif action == "call":
        if amount_owed == 0:
            return {"action": "check"}
        return {"action": "call"}

    else:
        if game_state["can_check"]:
            return {"action": "check"}
        return {"action": "fold"}




# ─────────────────────────────────────────────────────────────────────────
