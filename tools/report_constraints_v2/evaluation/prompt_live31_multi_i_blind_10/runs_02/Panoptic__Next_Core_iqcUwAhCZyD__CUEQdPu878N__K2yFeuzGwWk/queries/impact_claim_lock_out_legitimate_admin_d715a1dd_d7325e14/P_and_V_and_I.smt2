; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce2cc69ca_admin_set_by_init () Bool)
(declare-fun ce2cc69ca_init_called_by_factory () Bool)
(declare-fun ce2cc69ca_init_caller_authorized () Bool)
(declare-fun ce2cc69ca_legitimate_admin_locked_out () Bool)
(declare-fun ce2cc69ca_wallet_deployed () Bool)
(assert
 (= ce2cc69ca_admin_set_by_init ce2cc69ca_admin_set_by_init))
(assert
 (= ce2cc69ca_init_called_by_factory ce2cc69ca_init_called_by_factory))
(assert
 (= ce2cc69ca_init_caller_authorized ce2cc69ca_init_caller_authorized))
(assert
 (= ce2cc69ca_legitimate_admin_locked_out ce2cc69ca_legitimate_admin_locked_out))
(assert
 (= ce2cc69ca_wallet_deployed ce2cc69ca_wallet_deployed))
(define-fun report_preconditions () Bool (and ce2cc69ca_wallet_deployed ce2cc69ca_init_called_by_factory))
(define-fun report_safety () Bool (=> ce2cc69ca_legitimate_admin_locked_out
    (=> ce2cc69ca_admin_set_by_init ce2cc69ca_init_caller_authorized)))
(define-fun report_effects () Bool (and ce2cc69ca_legitimate_admin_locked_out
     ce2cc69ca_admin_set_by_init
     (not ce2cc69ca_init_caller_authorized)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
