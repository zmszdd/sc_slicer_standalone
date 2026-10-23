; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7087ac53_userop_reaches_validation () Bool)
(declare-fun c7087ac53_wallet_is_claimed () Bool)
(declare-fun c7087ac53_warden_userop_submission_blocked () Bool)
(assert
 (= c7087ac53_userop_reaches_validation c7087ac53_userop_reaches_validation))
(assert
 (= c7087ac53_wallet_is_claimed c7087ac53_wallet_is_claimed))
(assert
 (= c7087ac53_warden_userop_submission_blocked c7087ac53_warden_userop_submission_blocked))
(define-fun report_preconditions () Bool (and (not c7087ac53_wallet_is_claimed) c7087ac53_userop_reaches_validation))
(define-fun report_safety () Bool (=> (and (not c7087ac53_wallet_is_claimed) c7087ac53_userop_reaches_validation)
    (not c7087ac53_warden_userop_submission_blocked)))
(define-fun report_effects () Bool (and (not c7087ac53_wallet_is_claimed)
     c7087ac53_userop_reaches_validation
     (not (not c7087ac53_warden_userop_submission_blocked))))
