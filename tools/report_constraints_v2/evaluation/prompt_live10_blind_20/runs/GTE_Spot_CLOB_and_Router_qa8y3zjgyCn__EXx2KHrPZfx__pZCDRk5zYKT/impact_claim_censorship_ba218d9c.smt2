; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca0da2da7_cap_counts_only_active () Bool)
(declare-fun ca0da2da7_cap_enforced_flag () Bool)
(declare-fun ca0da2da7_expired_orders_resident () Bool)
(declare-fun ca0da2da7_selective_denial () Bool)
(assert
 (= ca0da2da7_cap_counts_only_active ca0da2da7_cap_counts_only_active))
(assert
 (= ca0da2da7_cap_enforced_flag ca0da2da7_cap_enforced_flag))
(assert
 (= ca0da2da7_expired_orders_resident ca0da2da7_expired_orders_resident))
(assert
 (= ca0da2da7_selective_denial ca0da2da7_selective_denial))
(define-fun report_preconditions () Bool (and ca0da2da7_cap_enforced_flag ca0da2da7_expired_orders_resident))
(define-fun report_safety () Bool (=> (and ca0da2da7_cap_enforced_flag ca0da2da7_expired_orders_resident)
    (and ca0da2da7_cap_counts_only_active (not ca0da2da7_selective_denial))))
(define-fun report_effects () Bool (and ca0da2da7_cap_enforced_flag
     ca0da2da7_expired_orders_resident
     (not (and ca0da2da7_cap_counts_only_active
               (not ca0da2da7_selective_denial)))))
