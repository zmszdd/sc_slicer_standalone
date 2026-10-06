; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun user_owns_existing_order () Bool)
(declare-fun order_is_post_only () Bool)
(declare-fun amended_price_would_fill () Bool)
(declare-fun amend_completed () Bool)
(assert
 (= user_owns_existing_order user_owns_existing_order))
(assert
 (= order_is_post_only order_is_post_only))
(assert
 (= amended_price_would_fill amended_price_would_fill))
(assert
 (= amend_completed amend_completed))
(define-fun report_preconditions () Bool (and user_owns_existing_order order_is_post_only amended_price_would_fill))
(define-fun report_safety () Bool (=> (and user_owns_existing_order order_is_post_only amended_price_would_fill)
    amend_completed))
(define-fun report_effects () Bool (and user_owns_existing_order
     order_is_post_only
     amended_price_would_fill
     (not amend_completed)))
(assert report_preconditions)
(check-sat)
(get-model)
