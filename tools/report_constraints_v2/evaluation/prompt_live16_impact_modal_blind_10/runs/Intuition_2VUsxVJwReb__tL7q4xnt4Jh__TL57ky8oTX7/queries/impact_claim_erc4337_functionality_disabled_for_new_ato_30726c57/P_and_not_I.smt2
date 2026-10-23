; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca1765b4f_erc4337_functionality_disabled () Bool)
(declare-fun ca1765b4f_userop_reaches_validation () Bool)
(declare-fun ca1765b4f_wallet_is_claimed () Bool)
(assert
 (= ca1765b4f_erc4337_functionality_disabled ca1765b4f_erc4337_functionality_disabled))
(assert
 (= ca1765b4f_userop_reaches_validation ca1765b4f_userop_reaches_validation))
(assert
 (= ca1765b4f_wallet_is_claimed ca1765b4f_wallet_is_claimed))
(define-fun report_preconditions () Bool (and (not ca1765b4f_wallet_is_claimed) ca1765b4f_userop_reaches_validation))
(define-fun report_safety () Bool (=> (and (not ca1765b4f_wallet_is_claimed) ca1765b4f_userop_reaches_validation)
    (not ca1765b4f_erc4337_functionality_disabled)))
(define-fun report_effects () Bool (and (not ca1765b4f_wallet_is_claimed)
     ca1765b4f_userop_reaches_validation
     (not (not ca1765b4f_erc4337_functionality_disabled))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
