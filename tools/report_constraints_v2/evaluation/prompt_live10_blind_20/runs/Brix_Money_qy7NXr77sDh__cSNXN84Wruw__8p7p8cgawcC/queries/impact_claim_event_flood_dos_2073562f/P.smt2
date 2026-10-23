; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbd169fbd_any_address_trigger () Bool)
(declare-fun cbd169fbd_custodian_event_flooded () Bool)
(declare-fun cbd169fbd_rebalance_callable_by_any_address () Bool)
(declare-fun cbd169fbd_repeated_calls_unlimited () Bool)
(assert
 (= cbd169fbd_any_address_trigger cbd169fbd_any_address_trigger))
(assert
 (= cbd169fbd_custodian_event_flooded cbd169fbd_custodian_event_flooded))
(assert
 (= cbd169fbd_rebalance_callable_by_any_address cbd169fbd_rebalance_callable_by_any_address))
(assert
 (= cbd169fbd_repeated_calls_unlimited cbd169fbd_repeated_calls_unlimited))
(define-fun report_preconditions () Bool (and cbd169fbd_rebalance_callable_by_any_address
     cbd169fbd_repeated_calls_unlimited
     cbd169fbd_any_address_trigger))
(define-fun report_safety () Bool (=> (and cbd169fbd_rebalance_callable_by_any_address
         cbd169fbd_repeated_calls_unlimited
         cbd169fbd_any_address_trigger)
    (not cbd169fbd_custodian_event_flooded)))
(define-fun report_effects () Bool (and cbd169fbd_rebalance_callable_by_any_address
     cbd169fbd_repeated_calls_unlimited
     cbd169fbd_any_address_trigger
     (not (not cbd169fbd_custodian_event_flooded))))
(assert report_preconditions)
(check-sat)
(get-model)
