; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun initial_supply () Int)
(declare-fun alice_deposit_amount () Int)
(declare-fun epoch () Int)
(declare-fun nav_includes_balance () Bool)
(declare-fun shares_received () Int)
(assert
 (= initial_supply initial_supply))
(assert
 (= alice_deposit_amount alice_deposit_amount))
(assert
 (= epoch epoch))
(assert
 (= nav_includes_balance nav_includes_balance))
(assert
 (= shares_received shares_received))
(define-fun report_preconditions () Bool (and (= 1000000 initial_supply)
     (= 1000000000000000000 alice_deposit_amount)
     (= 0 epoch)
     nav_includes_balance))
(define-fun report_safety () Bool (=> (and (= 0 epoch) (< 0 alice_deposit_amount) nav_includes_balance)
    (< 0 shares_received)))
(define-fun report_effects () Bool (and (= 0 epoch)
     (< 0 alice_deposit_amount)
     nav_includes_balance
     (not (< 0 shares_received))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
