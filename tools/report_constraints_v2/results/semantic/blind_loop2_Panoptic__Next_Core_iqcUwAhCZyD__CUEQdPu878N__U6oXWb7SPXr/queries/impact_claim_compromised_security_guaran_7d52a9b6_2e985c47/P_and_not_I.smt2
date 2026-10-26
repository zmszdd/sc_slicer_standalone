; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5be80d0e_caller_is_factory () Bool)
(declare-fun c5be80d0e_init_called () Bool)
(declare-fun c5be80d0e_init_publicly_callable () Bool)
(declare-fun c5be80d0e_init_reinit_protected () Bool)
(declare-fun c5be80d0e_security_guarantees_compromised () Bool)
(assert
 (= c5be80d0e_caller_is_factory c5be80d0e_caller_is_factory))
(assert
 (= c5be80d0e_init_called c5be80d0e_init_called))
(assert
 (= c5be80d0e_init_publicly_callable c5be80d0e_init_publicly_callable))
(assert
 (= c5be80d0e_init_reinit_protected c5be80d0e_init_reinit_protected))
(assert
 (= c5be80d0e_security_guarantees_compromised c5be80d0e_security_guarantees_compromised))
(define-fun report_preconditions () Bool (and c5be80d0e_init_called
     c5be80d0e_init_publicly_callable
     (not c5be80d0e_caller_is_factory)
     (not c5be80d0e_init_reinit_protected)))
(define-fun report_safety () Bool (=> c5be80d0e_init_called c5be80d0e_caller_is_factory))
(define-fun report_effects () Bool c5be80d0e_security_guarantees_compromised)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
