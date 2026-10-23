; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c435231ac_userop_reaches_validation () Bool)
(declare-fun c435231ac_wallet_is_claimed () Bool)
(declare-fun c435231ac_wallet_usable_as_smart_account () Bool)
(assert
 (= c435231ac_userop_reaches_validation c435231ac_userop_reaches_validation))
(assert
 (= c435231ac_wallet_is_claimed c435231ac_wallet_is_claimed))
(assert
 (= c435231ac_wallet_usable_as_smart_account c435231ac_wallet_usable_as_smart_account))
(define-fun report_preconditions () Bool (and (not c435231ac_wallet_is_claimed) c435231ac_userop_reaches_validation))
(define-fun report_safety () Bool (=> (and (not c435231ac_wallet_is_claimed) c435231ac_userop_reaches_validation)
    c435231ac_wallet_usable_as_smart_account))
(define-fun report_effects () Bool (and (not c435231ac_wallet_is_claimed)
     c435231ac_userop_reaches_validation
     (not c435231ac_wallet_usable_as_smart_account)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
