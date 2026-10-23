; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0e526628_alice_market_value_exceeds_basis () Bool)
(declare-fun c0e526628_bob_position_at_loss () Bool)
(declare-fun c0e526628_performance_fee_charged () Bool)
(declare-fun c0e526628_systematic_fee_evasion_occurs () Bool)
(declare-fun c0e526628_users_collude () Bool)
(assert
 (= c0e526628_alice_market_value_exceeds_basis c0e526628_alice_market_value_exceeds_basis))
(assert
 (= c0e526628_bob_position_at_loss c0e526628_bob_position_at_loss))
(assert
 (= c0e526628_performance_fee_charged c0e526628_performance_fee_charged))
(assert
 (= c0e526628_systematic_fee_evasion_occurs c0e526628_systematic_fee_evasion_occurs))
(assert
 (= c0e526628_users_collude c0e526628_users_collude))
(define-fun report_preconditions () Bool (and c0e526628_alice_market_value_exceeds_basis
     c0e526628_bob_position_at_loss
     c0e526628_users_collude))
(define-fun report_safety () Bool (=> (and c0e526628_alice_market_value_exceeds_basis
         c0e526628_bob_position_at_loss
         c0e526628_users_collude)
    (and c0e526628_performance_fee_charged
         (not c0e526628_systematic_fee_evasion_occurs))))
(define-fun report_effects () Bool (and c0e526628_alice_market_value_exceeds_basis
     c0e526628_bob_position_at_loss
     c0e526628_users_collude
     (not (and c0e526628_performance_fee_charged
               (not c0e526628_systematic_fee_evasion_occurs)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
