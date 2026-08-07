# Disclaimer

## No guarantees

This tool computes **theoretical expected value (EV)** and **simulated
probability estimates** from odds/price data you provide. These are
long-run mathematical averages and Monte Carlo estimates — they are **not**
predictions of, or guarantees about, any individual outcome. Short-run
results (a single open, a single session, even hundreds of opens) can and
routinely do differ substantially from the theoretical EV due to variance.
Nothing in this tool, its output, or its documentation should be
interpreted as a promise of profit or a "system" that beats the odds.

## Scope of this tool

This tool:
- Performs arithmetic (EV, RTP, variance, standard deviation) and
  Monte Carlo simulation on data **you supply**.
- Provides a bankroll/risk calculator that estimates probabilities of
  exceeding a stated loss limit, again purely from simulation of the odds
  you provided.
- Lets you log your own historical opening results locally and compares
  them to the theoretical EV.

This tool does **not**, anywhere in its code:
- Connect to, scrape, query, or automate Skin.Club or any other
  case-opening/gambling platform.
- Place bets, open cases, deposit funds, withdraw funds, or perform any
  other account action on any platform.
- Attempt to predict, influence, exploit, or manipulate any random-number
  generator or game outcome.
- Store, transmit, or require any account credentials for any external
  platform.

## Data sourcing requirement

You are responsible for how you obtain any case/odds/price data you enter
or import into this tool. Only use:
- Odds, drop-rate, or pricing information a platform has **itself
  published publicly** (e.g. a disclosed odds table), or
- Your **own** account/transaction history, which you are legally
  entitled to access.

Do not use this tool with data obtained by scraping, automated querying,
or any method that would violate a platform's terms of service or
applicable law. The bundled `data/sample_cases.json` is illustrative demo
data only and is not sourced from, or representative of, any specific
real platform's actual odds.

## Gambling risk

Case-opening / loot-box mechanics are gambling or gambling-adjacent
activities in many jurisdictions. Commercial case-opening products are
typically designed with a built-in house edge (return-to-player under
100%), meaning the operator profits on average across all players even
though individual players can and do win big on individual opens. No
calculator, bankroll strategy, or amount of analysis changes the sign of
a negative expected value over the long run — it can only help you decide
how much you're willing to risk, and for how long, before you start.

If you choose to spend money on these products:
- Only spend money you can fully afford to lose.
- Set a real budget and a real stop-loss before you start, and honor it
  regardless of what happens in the moment.
- Confirm that using such a service is legal in your jurisdiction and
  permitted for your age group.
- Confirm your use complies with the platform's own terms of service.

If gambling-like spending is becoming a problem for you or someone you
know, help is available:
- National Council on Problem Gambling (US): https://www.ncpgambling.org/ , 1-800-522-4700
- BeGambleAware (UK): https://www.begambleaware.org/
- GambleAware / local equivalents exist in most countries — search for
  your national problem-gambling helpline.

## No professional advice

This tool and its output do not constitute financial, legal, or gambling
advice. It is a general-purpose calculator provided as-is, with no
warranty of accuracy, for educational and personal decision-support
purposes only.
