; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb25aeb37_alice_market_value_exceeds_basis () Bool)
(declare-fun cb25aeb37_bob_position_at_loss () Bool)
(declare-fun cb25aeb37_collusion_present () Bool)
(declare-fun cb25aeb37_loss_trading_market_created () Bool)
(assert
 (= cb25aeb37_alice_market_value_exceeds_basis cb25aeb37_alice_market_value_exceeds_basis))
(assert
 (= cb25aeb37_bob_position_at_loss cb25aeb37_bob_position_at_loss))
(assert
 (= cb25aeb37_collusion_present cb25aeb37_collusion_present))
(assert
 (= cb25aeb37_loss_trading_market_created cb25aeb37_loss_trading_market_created))
(define-fun report_preconditions () Bool (and cb25aeb37_alice_market_value_exceeds_basis
     cb25aeb37_bob_position_at_loss
     cb25aeb37_collusion_present))
(define-fun report_safety () Bool (=> (and cb25aeb37_alice_market_value_exceeds_basis
         cb25aeb37_bob_position_at_loss
         cb25aeb37_collusion_present)
    (not cb25aeb37_loss_trading_market_created)))
(define-fun report_effects () Bool (and cb25aeb37_alice_market_value_exceeds_basis
     cb25aeb37_bob_position_at_loss
     cb25aeb37_collusion_present
     (not (not cb25aeb37_loss_trading_market_created))))
