; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb25aeb37_alice_basis () Int)
(declare-fun cb25aeb37_alice_market_value () Int)
(declare-fun cb25aeb37_bob_basis () Int)
(declare-fun cb25aeb37_bob_market_value () Int)
(declare-fun cb25aeb37_fee_charged_on_profitable_withdrawal () Bool)
(declare-fun cb25aeb37_loss_basis_market_created () Bool)
(assert
 (= cb25aeb37_alice_basis cb25aeb37_alice_basis))
(assert
 (= cb25aeb37_alice_market_value cb25aeb37_alice_market_value))
(assert
 (= cb25aeb37_bob_basis cb25aeb37_bob_basis))
(assert
 (= cb25aeb37_bob_market_value cb25aeb37_bob_market_value))
(assert
 (= cb25aeb37_fee_charged_on_profitable_withdrawal cb25aeb37_fee_charged_on_profitable_withdrawal))
(assert
 (= cb25aeb37_loss_basis_market_created cb25aeb37_loss_basis_market_created))
(define-fun report_preconditions () Bool (and (> cb25aeb37_alice_market_value cb25aeb37_alice_basis)
     (> cb25aeb37_bob_basis cb25aeb37_bob_market_value)))
(define-fun report_safety () Bool (=> (and (> cb25aeb37_alice_market_value cb25aeb37_alice_basis)
         (> cb25aeb37_bob_basis cb25aeb37_bob_market_value))
    (and cb25aeb37_fee_charged_on_profitable_withdrawal
         (not cb25aeb37_loss_basis_market_created))))
(define-fun report_effects () Bool (and (> cb25aeb37_alice_market_value cb25aeb37_alice_basis)
     (> cb25aeb37_bob_basis cb25aeb37_bob_market_value)
     (not (and cb25aeb37_fee_charged_on_profitable_withdrawal
               (not cb25aeb37_loss_basis_market_created)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
