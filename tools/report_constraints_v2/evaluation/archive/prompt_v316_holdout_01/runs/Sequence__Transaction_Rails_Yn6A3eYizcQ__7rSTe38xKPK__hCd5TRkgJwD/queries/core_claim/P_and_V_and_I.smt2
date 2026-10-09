; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun router_publicly_callable () Bool)
(declare-fun router_funds_nonzero () Bool)
(declare-fun caller_authorized () Bool)
(declare-fun funds_moved_to_arbitrary_target () Bool)
(assert
 (= router_publicly_callable router_publicly_callable))
(assert
 (= router_funds_nonzero router_funds_nonzero))
(assert
 (= caller_authorized caller_authorized))
(assert
 (= funds_moved_to_arbitrary_target funds_moved_to_arbitrary_target))
(define-fun report_preconditions () Bool (and router_publicly_callable
     router_publicly_callable
     router_funds_nonzero
     (not caller_authorized)))
(define-fun report_safety () Bool (=> (and router_funds_nonzero (not caller_authorized))
    (not funds_moved_to_arbitrary_target)))
(define-fun report_effects () Bool (and router_funds_nonzero
     (not caller_authorized)
     (not (not funds_moved_to_arbitrary_target))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
